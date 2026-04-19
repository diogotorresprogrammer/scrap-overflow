import { Component, Input } from '@angular/core';
import { FormsModule } from '@angular/forms';
import {
  IonItem, IonLabel, IonInput, IonItemDivider, IonToggle, IonNote,
} from '@ionic/angular/standalone';
import { TranslatePipe } from '@ngx-translate/core';
import { ScrapItem } from '../../services/api.service';

@Component({
  selector: 'app-detail-lumber',
  templateUrl: 'detail-lumber.component.html',
  standalone: true,
  imports: [FormsModule, TranslatePipe, IonItem, IonLabel, IonInput, IonItemDivider, IonToggle, IonNote],
})
export class DetailLumberComponent {
  @Input() item!: ScrapItem;
  @Input() draft!: Partial<ScrapItem>;
  @Input() editing = false;
}
