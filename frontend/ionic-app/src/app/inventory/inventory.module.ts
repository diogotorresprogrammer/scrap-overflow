import { IonicModule } from '@ionic/angular';
import { NgModule } from '@angular/core';
import { CommonModule } from '@angular/common';
import { FormsModule } from '@angular/forms';
import { InventoryPage } from './inventory.page';
import { InventoryPageRoutingModule } from './inventory-routing.module';

@NgModule({
  imports: [
    IonicModule,
    CommonModule,
    FormsModule,
    InventoryPageRoutingModule
  ],
  declarations: [InventoryPage]
})
export class InventoryPageModule {}
