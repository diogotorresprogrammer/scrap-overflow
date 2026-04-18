import { Component } from '@angular/core';
import { FormsModule } from '@angular/forms';
import { Router } from '@angular/router';
import {
  IonContent, IonIcon, IonCard, IonSegment, IonSegmentButton,
  IonItem, IonLabel, IonInput, IonButton,
  ToastController, LoadingController,
} from '@ionic/angular/standalone';
import { AuthService } from '../services/auth.service';

@Component({
  selector: 'app-landing',
  templateUrl: 'landing.page.html',
  styleUrls: ['landing.page.scss'],
  standalone: true,
  imports: [
    FormsModule,
    IonContent, IonIcon, IonCard, IonSegment, IonSegmentButton,
    IonItem, IonLabel, IonInput, IonButton,
  ],
})
export class LandingPage {
  mode: 'login' | 'register' = 'login';

  email    = '';
  password = '';
  username = '';

  constructor(
    private auth: AuthService,
    private router: Router,
    private toast: ToastController,
    private loading: LoadingController,
  ) {}

  async submit() {
    const loader = await this.loading.create({ message: this.mode === 'login' ? 'Signing in...' : 'Creating account...' });
    await loader.present();

    const obs = this.mode === 'login'
      ? this.auth.login(this.email, this.password)
      : this.auth.register(this.username, this.email, this.password);

    obs.subscribe({
      next: async () => {
        await loader.dismiss();
        this.router.navigate(['/tabs/inventory'], { replaceUrl: true });
      },
      error: async (err) => {
        await loader.dismiss();
        const msg = err.error?.description ?? (this.mode === 'login' ? 'Invalid email or password.' : 'Registration failed.');
        const t = await this.toast.create({ message: msg, duration: 3000, color: 'danger' });
        await t.present();
      },
    });
  }
}
