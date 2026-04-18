import { Component } from '@angular/core';
import { DecimalPipe } from '@angular/common';
import { FormsModule } from '@angular/forms';
import { Camera, CameraResultType, CameraSource } from '@capacitor/camera';
import { Geolocation } from '@capacitor/geolocation';
import {
  IonHeader, IonToolbar, IonTitle, IonContent, IonItem, IonLabel,
  IonSelect, IonSelectOption, IonInput, IonTextarea, IonItemDivider,
  IonToggle, IonButton, IonIcon, IonSpinner,
  NavController, ToastController,
} from '@ionic/angular/standalone';
import { ApiService, ItemType, ScrapItem } from '../services/api.service';

@Component({
  selector: 'app-add',
  templateUrl: 'add.page.html',
  styleUrls: ['add.page.scss'],
  standalone: true,
  imports: [
    FormsModule, DecimalPipe,
    IonHeader, IonToolbar, IonTitle, IonContent, IonItem, IonLabel,
    IonSelect, IonSelectOption, IonInput, IonTextarea, IonItemDivider,
    IonToggle, IonButton, IonIcon, IonSpinner,
  ],
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

  save() {
    if (!this.item.name) return;
    this.saving = true;
    this.api.createItem(this.item).subscribe({
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
