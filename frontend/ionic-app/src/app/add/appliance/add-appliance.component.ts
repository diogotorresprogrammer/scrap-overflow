import { Component, Input } from '@angular/core';
import { FormsModule } from '@angular/forms';
import {
  IonItem, IonLabel, IonInput, IonItemDivider, IonSelect, IonSelectOption,
} from '@ionic/angular/standalone';
import { TranslatePipe } from '@ngx-translate/core';
import { ScrapItem } from '../../services/api.service';

@Component({
  selector: 'app-add-appliance',
  templateUrl: 'add-appliance.component.html',
  standalone: true,
  imports: [FormsModule, TranslatePipe, IonItem, IonLabel, IonInput, IonItemDivider, IonSelect, IonSelectOption],
})
export class AddApplianceComponent {
  @Input() item!: Partial<ScrapItem>;
}
