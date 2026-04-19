import { Component } from '@angular/core';
import { FormsModule } from '@angular/forms';
import { Router } from '@angular/router';
import {
  IonHeader, IonToolbar, IonTitle, IonButtons, IonButton, IonIcon,
  IonContent, IonSpinner, IonList, IonItemSliding, IonItem, IonThumbnail,
  IonLabel, IonBadge, IonItemOptions, IonItemOption,
  IonSelect, IonSelectOption,
  AlertController, ToastController,
} from '@ionic/angular/standalone';
import { TranslatePipe, TranslateService } from '@ngx-translate/core';
import { ApiService, ScrapItem, SortField, SortOrder } from '../services/api.service';
import { AuthService } from '../services/auth.service';

@Component({
  selector: 'app-inventory',
  templateUrl: 'inventory.page.html',
  styleUrls: ['inventory.page.scss'],
  standalone: true,
  imports: [
    FormsModule, TranslatePipe,
    IonHeader, IonToolbar, IonTitle, IonButtons, IonButton, IonIcon,
    IonContent, IonSpinner, IonList, IonItemSliding, IonItem, IonThumbnail,
    IonLabel, IonBadge, IonItemOptions, IonItemOption,
    IonSelect, IonSelectOption,
  ],
})
export class InventoryPage {
  items: ScrapItem[] = [];
  loading = true;

  sort: SortField = 'created_at';
  order: SortOrder = 'desc';
  page = 1;
  readonly perPage = 10;
  total = 0;
  pages = 0;

  constructor(
    private api: ApiService,
    private auth: AuthService,
    private router: Router,
    private alertCtrl: AlertController,
    private toastCtrl: ToastController,
    private translate: TranslateService,
  ) {}

  ionViewWillEnter() {
    this.load();
  }

  load() {
    this.loading = true;
    this.api.getItems({ sort: this.sort, order: this.order, page: this.page, per_page: this.perPage }).subscribe({
      next: (res) => {
        this.items = res.items;
        this.total = res.total;
        this.pages = res.pages;
        this.loading = false;
      },
      error: () => { this.loading = false; },
    });
  }

  onSortChange() {
    this.page = 1;
    this.load();
  }

  toggleOrder() {
    this.order = this.order === 'desc' ? 'asc' : 'desc';
    this.page = 1;
    this.load();
  }

  changePage(p: number) {
    this.page = p;
    this.load();
  }

  goToDetail(item: ScrapItem) {
    this.router.navigate(['/tabs/inventory', item.id]);
  }

  async deleteItem(item: ScrapItem) {
    const alert = await this.alertCtrl.create({
      header: this.translate.instant('item-detail.delete-confirm-header'),
      message: this.translate.instant('item-detail.delete-confirm-message', { name: item.name }),
      buttons: [
        { text: this.translate.instant('common.cancel'), role: 'cancel' },
        {
          text: this.translate.instant('common.delete'), role: 'destructive',
          handler: () => {
            this.api.deleteItem(item.id!).subscribe({
              next: async () => {
                this.load();
                const t = await this.toastCtrl.create({
                  message: this.translate.instant('inventory.item-deleted'),
                  duration: 1500,
                });
                await t.present();
              },
            });
          },
        },
      ],
    });
    await alert.present();
  }

  async confirmLogout() {
    const alert = await this.alertCtrl.create({
      header: this.translate.instant('inventory.sign-out-confirm'),
      buttons: [
        { text: this.translate.instant('common.cancel'), role: 'cancel' },
        { text: this.translate.instant('common.sign-out'), role: 'destructive', handler: () => this.auth.logout() },
      ],
    });
    await alert.present();
  }

  typeColor(type: string | undefined): string {
    const map: Record<string, string> = {
      lumber: 'warning', metal: 'medium', furniture: 'tertiary', appliance: 'success',
    };
    return map[type ?? ''] ?? 'primary';
  }
}
