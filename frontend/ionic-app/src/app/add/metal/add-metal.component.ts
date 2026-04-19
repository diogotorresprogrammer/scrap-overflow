import { Component, Input } from '@angular/core';
import { FormsModule } from '@angular/forms';
import {
  IonItem, IonLabel, IonInput, IonItemDivider,
} from '@ionic/angular/standalone';
import { TranslatePipe } from '@ngx-translate/core';
import { ScrapItem } from '../../services/api.service';

@Component({
  selector: 'app-add-metal',
  templateUrl: 'add-metal.component.html',
  standalone: true,
  imports: [FormsModule, TranslatePipe, IonItem, IonLabel, IonInput, IonItemDivider],
})
export class AddMetalComponent {
  @Input() item!: Partial<ScrapItem>;
}
