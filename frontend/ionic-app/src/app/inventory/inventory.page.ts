import { Component } from '@angular/core';
import { Router } from '@angular/router';
import {
  IonHeader, IonToolbar, IonTitle, IonButtons, IonButton, IonIcon,
  IonContent, IonSpinner, IonList, IonItemSliding, IonItem, IonThumbnail,
  IonLabel, IonBadge, IonItemOptions, IonItemOption,
  AlertController, ToastController,
} from '@ionic/angular/standalone';
import { ApiService, ScrapItem } from '../services/api.service';
import { AuthService } from '../services/auth.service';

@Component({
  selector: 'app-inventory',
  templateUrl: 'inventory.page.html',
  styleUrls: ['inventory.page.scss'],
  standalone: true,
  imports: [
    IonHeader, IonToolbar, IonTitle, IonButtons, IonButton, IonIcon,
    IonContent, IonSpinner, IonList, IonItemSliding, IonItem, IonThumbnail,
    IonLabel, IonBadge, IonItemOptions, IonItemOption,
  ],
})
export class InventoryPage {
  items: ScrapItem[] = [];
  loading = true;

  constructor(
    private api: ApiService,
    private auth: AuthService,
    private router: Router,
    private alertCtrl: AlertController,
    private toastCtrl: ToastController,
  ) {}

  ionViewWillEnter() {
    this.load();
  }

  load() {
    this.loading = true;
    this.api.getItems().subscribe({
      next: (items) => { this.items = items; this.loading = false; },
      error: () => { this.loading = false; },
    });
  }

  goToDetail(item: ScrapItem) {
    this.router.navigate(['/tabs/inventory', item.id]);
  }

  async deleteItem(item: ScrapItem) {
    const alert = await this.alertCtrl.create({
      header: 'Delete item?',
      message: `"${item.name}" will be permanently removed.`,
      buttons: [
        { text: 'Cancel', role: 'cancel' },
        {
          text: 'Delete', role: 'destructive',
          handler: () => {
            this.api.deleteItem(item.id!).subscribe({
              next: async () => {
                this.items = this.items.filter(i => i.id !== item.id);
                const t = await this.toastCtrl.create({ message: 'Item deleted.', duration: 1500 });
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
      header: 'Sign out?',
      buttons: [
        { text: 'Cancel', role: 'cancel' },
        { text: 'Sign out', role: 'destructive', handler: () => this.auth.logout() },
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
