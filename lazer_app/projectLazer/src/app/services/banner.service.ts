import { Injectable } from '@angular/core';
import { Platform } from '@ionic/angular';

export interface Banner {
  content_html: string;
  color: 'pink' | 'green';
}

@Injectable({
  providedIn: 'root',
})
export class BannerService {
  banner: Banner | null = null;
  urlRoot: string = '';

  async fetchBanner(): Promise<void> {
    const url = `${this.urlRoot}/lazer/api/banner/`;
    try {
      const response = await fetch(url, {
        method: 'GET',
      });
      if (!response.ok) {
        this.banner = null;
        return;
      }

      const json = await response.json();
      if (json.content_html && json.color) {
        this.banner = {
          content_html: json.content_html,
          color: json.color,
        };
      } else {
        this.banner = null;
      }
    } catch (error) {
      console.error('Failed to fetch banner:', error);
      this.banner = null;
    }
  }

  constructor(private platform: Platform) {
    if (platform.is('hybrid')) {
      this.urlRoot = 'https://bikeaction.org';
    }
  }
}
