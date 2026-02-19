import { Component, inject } from '@angular/core';

import { OnlineStatusService } from '../services/online.service';
import { UpdateService } from '../services/update.service';
import { AccountService } from '../services/account.service';

@Component({
  selector: 'app-about',
  templateUrl: './about.page.html',
  styleUrls: ['./about.page.scss'],
  standalone: false,
})
export class AboutPage {
  accountService = inject(AccountService);
  onlineStatus = inject(OnlineStatusService);
  updateService = inject(UpdateService);
}
