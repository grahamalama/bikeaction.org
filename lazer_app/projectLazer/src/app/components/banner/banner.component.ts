import { Component, OnInit } from '@angular/core';

import { BannerService } from '../../services/banner.service';

@Component({
  selector: 'app-banner',
  templateUrl: 'banner.component.html',
  styleUrls: ['banner.component.scss'],
  standalone: true,
  imports: [],
})
export class BannerComponent implements OnInit {
  constructor(public bannerService: BannerService) {}

  ngOnInit() {
    this.bannerService.fetchBanner();
  }
}
