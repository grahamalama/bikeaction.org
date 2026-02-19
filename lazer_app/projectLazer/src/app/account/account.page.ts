import { Component, inject } from '@angular/core';

import { OnlineStatusService } from '../services/online.service';
import { UpdateService } from '../services/update.service';
import { AccountService } from '../services/account.service';

@Component({
  selector: 'app-account',
  templateUrl: './account.page.html',
  styleUrls: ['./account.page.scss'],
  standalone: false,
})
export class AccountPage {
  accountService = inject(AccountService);
  onlineStatus = inject(OnlineStatusService);
  updateService = inject(UpdateService);
}
