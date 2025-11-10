import csv
import re
import uuid
from datetime import datetime, timedelta

from django.contrib.auth import get_user_model
from django.core.management.base import BaseCommand
from django.db.models import Q

from facets.models import District, ZipCode
from membership.models import Membership

User = get_user_model()


class Command(BaseCommand):
    help = (
        "Export a voter list of members as of a given date. "
        "Users are considered members if they have: "
        "(1) an active Membership record, "
        "(2) Discord activity within 30 days, or "
        "(3) an active Stripe subscription."
    )

    def add_arguments(self, parser):
        parser.add_argument(
            "start_date",
            type=str,
            help=(
                "Start date for membership range (YYYY-MM-DD format). "
                "If end_date is not provided, checks membership as of this date."
            ),
        )
        parser.add_argument(
            "end_date",
            type=str,
            nargs="?",
            help=(
                "End date for membership range (YYYY-MM-DD format). "
                "If provided, exports members who were active at any point during the range."
            ),
        )
        parser.add_argument(
            "--output",
            type=str,
            default="voter_list.csv",
            help="Output CSV file path (default: voter_list.csv)",
        )
        parser.add_argument(
            "--kind",
            type=str,
            choices=["fiscal", "participation", "all"],
            default="all",
            help=(
                "Filter by membership kind for users with explicit Membership records "
                "(default: all). Note: This filter does not apply to Discord or Stripe members."
            ),
        )

    def handle(self, *args, **options):
        # Parse the dates
        start_date_str = options["start_date"]
        end_date_str = options.get("end_date")

        try:
            start_date = datetime.strptime(start_date_str, "%Y-%m-%d").date()
        except ValueError:
            self.stderr.write(
                self.style.ERROR(f"Invalid start date format: {start_date_str}. Use YYYY-MM-DD")
            )
            return

        # If end_date is provided, we're doing a range query
        if end_date_str:
            try:
                end_date = datetime.strptime(end_date_str, "%Y-%m-%d").date()
            except ValueError:
                self.stderr.write(
                    self.style.ERROR(f"Invalid end date format: {end_date_str}. Use YYYY-MM-DD")
                )
                return

            if end_date < start_date:
                self.stderr.write(self.style.ERROR("End date must be after start date"))
                return
        else:
            # Single date mode - treat as both start and end
            end_date = start_date

        output_file = options["output"]
        kind_filter = options["kind"]

        # Calculate the date range for Discord activity
        # For a range query, we check if they had activity between (start_date - 30) and end_date
        # For a single date, we check if they had activity between (date - 30) and date
        discord_activity_start = start_date - timedelta(days=30)
        discord_activity_end = end_date

        # Build query to find all users who are members during the date range
        # A user is a member if they meet ANY of these criteria:
        # 1. Have an explicit Membership record that overlaps with [start_date, end_date]
        # 2. Have Discord activity during the range (considering 30-day lookback)
        # 3. Have an active Stripe subscription (current status only)

        # Membership overlaps with date range if:
        # - membership starts before or during the range (start_date <= end_date)
        # - AND membership ends after or during the range
        #   (end_date >= start_date OR end_date is null)
        membership_record_query = Q(memberships__start_date__lte=end_date) & (
            Q(memberships__end_date__isnull=True) | Q(memberships__end_date__gte=start_date)
        )

        # Apply kind filter to membership records if specified
        if kind_filter == "fiscal":
            membership_record_query &= Q(memberships__kind=Membership.Kind.FISCAL)
        elif kind_filter == "participation":
            membership_record_query &= Q(memberships__kind=Membership.Kind.PARTICIPATION)

        # Discord activity within the date range (with 30-day lookback from start_date)
        discord_activity_query = Q(socialaccount__provider="discord") & Q(
            profile__discord_activity__date__gte=discord_activity_start,
            profile__discord_activity__date__lte=discord_activity_end,
        )

        # Note: For Stripe subscriptions, we're checking for currently active ones
        # since historical subscription status is harder to determine
        stripe_subscription_query = Q(djstripe_customers__subscriptions__status__in=["active"])

        # Combine all three criteria with OR
        members_query = (
            membership_record_query | discord_activity_query | stripe_subscription_query
        )

        # Get all users matching the criteria
        members = User.objects.filter(members_query).select_related("profile").distinct()

        self.stdout.write(f"Total users in database: {User.objects.count()}")
        if start_date == end_date:
            self.stdout.write(f"Members as of {start_date}: {members.count()}")
        else:
            self.stdout.write(
                f"Members active between {start_date} and {end_date}: {members.count()}"
            )

        # Prepare data for CSV export
        voter_data = []

        for user in members:
            email = user.email
            district_number = None

            # Get the district from the user's profile
            if hasattr(user, "profile") and user.profile:
                profile = user.profile

                # First try to get district from location (geocoded address)
                district_obj = profile.district
                if district_obj:
                    # Extract district number from name (e.g., "District 5" -> "5")
                    match = re.search(r"\d+", district_obj.name)
                    if match:
                        district_number = match.group()

                # If no district from location, try to infer from zip code
                if not district_number and profile.zip_code:
                    zip_code_str = profile.zip_code.strip()
                    # Look up the ZipCode facet
                    try:
                        zip_facet = ZipCode.objects.get(name=zip_code_str)
                        # Find districts that intersect with this zip code
                        # Use the centroid of the zip to find the most likely district
                        districts = District.objects.filter(mpoly__intersects=zip_facet.mpoly)
                        if districts.exists():
                            # If multiple districts, use the one containing the centroid
                            centroid = zip_facet.mpoly.centroid
                            district_from_centroid = districts.filter(
                                mpoly__contains=centroid
                            ).first()
                            if district_from_centroid:
                                district_obj = district_from_centroid
                            else:
                                # Fall back to first intersecting district
                                district_obj = districts.first()

                            # Extract district number
                            match = re.search(r"\d+", district_obj.name)
                            if match:
                                district_number = match.group()
                    except ZipCode.DoesNotExist:
                        # Zip code not in database, continue without district
                        pass

            # Password is the literal string "password,"
            password = "password,"

            # Generate a UUID for the unique_id
            user_uuid = str(uuid.uuid4())

            # Format unique_id as "dN-{UUID}" where N is the district number
            if district_number:
                unique_id = f"d{district_number}-{user_uuid}"
            else:
                # If no district, use d0
                unique_id = f"d0-{user_uuid}"

            # Get full name
            full_name = user.get_full_name() or ""

            voter_data.append(
                {
                    "password": password,
                    "unique_id": unique_id,
                    "email": email,
                    "full_name": full_name,
                }
            )

        # Write to CSV
        with open(output_file, "w", newline="") as csvfile:
            fieldnames = ["password", "unique_id", "email", "full_name"]
            writer = csv.DictWriter(csvfile, fieldnames=fieldnames)

            writer.writeheader()
            writer.writerows(voter_data)

        self.stdout.write(
            self.style.SUCCESS(f"Successfully exported {len(voter_data)} members to {output_file}")
        )
        if start_date == end_date:
            self.stdout.write(
                self.style.SUCCESS(f"Membership as of: {start_date.strftime('%Y-%m-%d')}")
            )
        else:
            start_str = start_date.strftime("%Y-%m-%d")
            end_str = end_date.strftime("%Y-%m-%d")
            self.stdout.write(self.style.SUCCESS(f"Membership range: {start_str} to {end_str}"))

        # Summary statistics
        with_district = sum(1 for row in voter_data if not row["unique_id"].startswith("d0-"))
        without_district = len(voter_data) - with_district

        self.stdout.write(self.style.SUCCESS(f"Members with district: {with_district}"))
        if without_district > 0:
            self.stdout.write(self.style.WARNING(f"Members without district: {without_district}"))
