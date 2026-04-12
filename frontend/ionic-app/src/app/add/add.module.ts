import { IonicModule } from '@ionic/angular';
import { NgModule } from '@angular/core';
import { CommonModule } from '@angular/common';
import { FormsModule } from '@angular/forms';
import { AddPage } from './add.page';
import { AddPageRoutingModule } from './add-routing.module';

@NgModule({
  imports: [
    IonicModule,
    CommonModule,
    FormsModule,
    AddPageRoutingModule
  ],
  declarations: [AddPage]
})
export class AddPageModule {}
