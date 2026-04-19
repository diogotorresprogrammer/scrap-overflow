import { Component, Input } from '@angular/core';
import { FormsModule } from '@angular/forms';
import {
  IonItem, IonLabel, IonInput, IonItemDivider, IonSelect, IonSelectOption, IonNote,
} from '@ionic/angular/standalone';
import { TranslatePipe } from '@ngx-translate/core';
import { ScrapItem } from '../../services/api.service';

@Component({
  selector: 'app-detail-appliance',
  templateUrl: 'detail-appliance.component.html',
  standalone: true,
  imports: [FormsModule, TranslatePipe, IonItem, IonLabel, IonInput, IonItemDivider, IonSelect, IonSelectOption, IonNote],
})
export class DetailApplianceComponent {
  @Input() item!: ScrapItem;
  @Input() draft!: Partial<ScrapItem>;
  @Input() editing = false;
}
