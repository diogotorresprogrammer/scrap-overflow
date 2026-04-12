import { Component } from '@angular/core';
import { Camera, CameraResultType, CameraSource } from '@capacitor/camera';
import { Geolocation } from '@capacitor/geolocation';
import { NavController, ToastController } from '@ionic/angular';
import { ApiService, ItemType, ScrapItem } from '../services/api.service';
import { UserService } from '../services/user.service';

@Component({
  selector: 'app-add',
  templateUrl: 'add.page.html',
  styleUrls: ['add.page.scss'],
  standalone: false,
})
export class AddPage {
  item: Partial<ScrapItem> = { item_type: 'lumber', dimension_unit: 'mm' };
  photoUrl: string | undefined;
  saving = false;

  readonly itemTypes: { value: ItemType; label: string }[] = [
    { value: 'lumber',    label: 'Lumber' },
    { value: 'metal',     label: 'Metal' },
    { value: 'furniture', label: 'Furniture' },
    { value: 'appliance', label: 'Appliance' },
  ];

  constructor(
    private api: ApiService,
    private user: UserService,
    private nav: NavController,
    private toast: ToastController,
  ) {}

  get type(): ItemType { return this.item.item_type ?? 'lumber'; }

  async takePhoto() {
    const photo = await Camera.getPhoto({
      resultType: CameraResultType.DataUrl,
      source: CameraSource.Camera,
      quality: 80,
    });
    this.photoUrl = photo.dataUrl;
    this.item.photo_url = photo.dataUrl;
  }

  async getLocation() {
    const pos = await Geolocation.getCurrentPosition();
    this.item.location_lat = pos.coords.latitude;
    this.item.location_lng = pos.coords.longitude;
  }

  async save() {
    if (!this.item.name) return;

    const userId = this.user.userId;
    if (!userId) {
      const t = await this.toast.create({
        message: 'No user set. Paste your user ID in the Inventory settings.',
        duration: 3000, color: 'danger',
      });
      await t.present();
      return;
    }

    this.saving = true;
    this.api.createItem({ ...this.item, user_id: userId }).subscribe({
      next: () => {
        this.saving = false;
        this.item = { item_type: 'lumber', dimension_unit: 'mm' };
        this.photoUrl = undefined;
        this.nav.navigateRoot('/tabs/inventory');
      },
      error: async () => {
        this.saving = false;
        const t = await this.toast.create({ message: 'Failed to save item.', duration: 2000, color: 'danger' });
        await t.present();
      },
    });
  }
}
