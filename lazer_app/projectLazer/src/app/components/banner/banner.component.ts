import { Component, OnInit, inject } from '@angular/core';

import { BannerService } from '../../services/banner.service';

@Component({
  selector: 'app-banner',
  templateUrl: 'banner.component.html',
  styleUrls: ['banner.component.scss'],
  standalone: true,
  imports: [],
})
export class BannerComponent implements OnInit {
  bannerService = inject(BannerService);


  ngOnInit() {
    this.bannerService.fetchBanner();
  }
}
