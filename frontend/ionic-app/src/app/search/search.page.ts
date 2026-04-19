import { Component } from '@angular/core';
import { FormsModule } from '@angular/forms';
import {
  IonHeader, IonToolbar, IonTitle, IonContent, IonSearchbar,
  IonList, IonItem, IonThumbnail, IonLabel, IonBadge,
} from '@ionic/angular/standalone';
import { TranslatePipe } from '@ngx-translate/core';
import { ApiService, ScrapItem } from '../services/api.service';

@Component({
  selector: 'app-search',
  templateUrl: 'search.page.html',
  styleUrls: ['search.page.scss'],
  standalone: true,
  imports: [
    FormsModule, TranslatePipe,
    IonHeader, IonToolbar, IonTitle, IonContent, IonSearchbar,
    IonList, IonItem, IonThumbnail, IonLabel, IonBadge,
  ],
})
export class SearchPage {
  query = '';
  results: ScrapItem[] = [];
  private allItems: ScrapItem[] = [];

  constructor(private api: ApiService) {}

  ionViewWillEnter() {
    this.api.getItems({ per_page: 1000 }).subscribe(res => {
      this.allItems = res.items;
      this.filter();
    });
  }

  filter() {
    const q = this.query.toLowerCase();
    if (!q) { this.results = this.allItems; return; }
    this.results = this.allItems.filter(item =>
      item.name.toLowerCase().includes(q) ||
      item.description?.toLowerCase().includes(q) ||
      item.dimension_raw?.toLowerCase().includes(q) ||
      item.tags?.some(t => t.toLowerCase().includes(q))
    );
  }
}
