import { Component, Input } from '@angular/core';
import { FormsModule } from '@angular/forms';
import {
  IonItem, IonLabel, IonInput, IonItemDivider, IonToggle,
} from '@ionic/angular/standalone';
import { TranslatePipe } from '@ngx-translate/core';
import { ScrapItem } from '../../services/api.service';

@Component({
  selector: 'app-add-furniture',
  templateUrl: 'add-furniture.component.html',
  standalone: true,
  imports: [FormsModule, TranslatePipe, IonItem, IonLabel, IonInput, IonItemDivider, IonToggle],
})
export class AddFurnitureComponent {
  @Input() item!: Partial<ScrapItem>;
}
