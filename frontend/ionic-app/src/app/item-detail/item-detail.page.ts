import { Component, OnInit } from '@angular/core';
import { DatePipe, DecimalPipe } from '@angular/common';
import { FormsModule } from '@angular/forms';
import { ActivatedRoute } from '@angular/router';
import {
  IonHeader, IonToolbar, IonButtons, IonBackButton, IonTitle, IonButton,
  IonIcon, IonSpinner, IonContent, IonList, IonItem, IonLabel, IonBadge,
  IonInput, IonTextarea, IonSelect, IonSelectOption, IonItemDivider,
  IonNote,
  AlertController, NavController, ToastController,
} from '@ionic/angular/standalone';
import { TranslatePipe, TranslateService } from '@ngx-translate/core';
import { ApiService, ScrapItem } from '../services/api.service';
import { DetailLumberComponent } from './lumber/detail-lumber.component';
import { DetailMetalComponent } from './metal/detail-metal.component';
import { DetailFurnitureComponent } from './furniture/detail-furniture.component';
import { DetailApplianceComponent } from './appliance/detail-appliance.component';

@Component({
  selector: 'app-item-detail',
  templateUrl: 'item-detail.page.html',
  styleUrls: ['item-detail.page.scss'],
  standalone: true,
  imports: [
    FormsModule, DatePipe, DecimalPipe, TranslatePipe,
    IonHeader, IonToolbar, IonButtons, IonBackButton, IonTitle, IonButton,
    IonIcon, IonSpinner, IonContent, IonList, IonItem, IonLabel, IonBadge,
    IonInput, IonTextarea, IonSelect, IonSelectOption, IonItemDivider,
    IonNote,
    DetailLumberComponent, DetailMetalComponent, DetailFurnitureComponent, DetailApplianceComponent,
  ],
})
export class ItemDetailPage implements OnInit {
  item: ScrapItem | null = null;
  draft: Partial<ScrapItem> = {};
  loading = true;
  saving = false;
  editing = false;

  constructor(
    private route: ActivatedRoute,
    private api: ApiService,
    private nav: NavController,
    private alertCtrl: AlertController,
    private toastCtrl: ToastController,
    private translate: TranslateService,
  ) {}

  ngOnInit() {
    const id = this.route.snapshot.paramMap.get('id')!;
    this.api.getItem(id).subscribe({
      next: (item) => { this.item = item; this.loading = false; },
      error: () => { this.loading = false; },
    });
  }

  startEdit() {
    this.draft = { ...this.item };
    this.editing = true;
  }

  cancelEdit() {
    this.editing = false;
    this.draft = {};
  }

  save() {
    this.saving = true;
    this.api.updateItem(this.item!.id!, this.draft).subscribe({
      next: async (updated) => {
        this.item = updated;
        this.editing = false;
        this.saving = false;
        const t = await this.toastCtrl.create({
          message: this.translate.instant('item-detail.saved'),
          duration: 1500,
        });
        await t.present();
      },
      error: () => { this.saving = false; },
    });
  }

  async confirmDelete() {
    const alert = await this.alertCtrl.create({
      header: this.translate.instant('item-detail.delete-confirm-header'),
      message: this.translate.instant('item-detail.delete-confirm-message', { name: this.item!.name }),
      buttons: [
        { text: this.translate.instant('common.cancel'), role: 'cancel' },
        { text: this.translate.instant('common.delete'), role: 'destructive', handler: () => this.delete() },
      ],
    });
    await alert.present();
  }

  private delete() {
    this.api.deleteItem(this.item!.id!).subscribe({
      next: () => this.nav.navigateBack('/tabs/inventory'),
    });
  }

  typeColor(type: string | undefined): string {
    const map: Record<string, string> = {
      lumber: 'warning', metal: 'medium', furniture: 'tertiary', appliance: 'success',
    };
    return map[type ?? ''] ?? 'primary';
  }
}
