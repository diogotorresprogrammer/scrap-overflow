import { Component } from '@angular/core';
import { Router } from '@angular/router';
import { AlertController, ToastController } from '@ionic/angular';
import { ApiService, ScrapItem } from '../services/api.service';
import { UserService } from '../services/user.service';

@Component({
  selector: 'app-inventory',
  templateUrl: 'inventory.page.html',
  styleUrls: ['inventory.page.scss'],
  standalone: false,
})
export class InventoryPage {
  items: ScrapItem[] = [];
  loading = true;

  constructor(
    private api: ApiService,
    private user: UserService,
    private router: Router,
    private alertCtrl: AlertController,
    private toastCtrl: ToastController,
  ) {}

  ionViewWillEnter() {
    this.load();
  }

  load() {
    this.loading = true;
    this.api.getItems({ user_id: this.user.userId ?? undefined }).subscribe({
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

  async promptUserId() {
    const alert = await this.alertCtrl.create({
      header: 'Set user ID',
      message: 'Paste the UUID from when you created your user.',
      inputs: [{ name: 'uid', placeholder: 'xxxxxxxx-xxxx-xxxx-xxxx-xxxxxxxxxxxx', value: this.user.userId ?? '' }],
      buttons: [
        { text: 'Cancel', role: 'cancel' },
        {
          text: 'Save',
          handler: (d) => {
            if (d.uid?.trim()) { this.user.set(d.uid.trim()); this.load(); }
          },
        },
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
