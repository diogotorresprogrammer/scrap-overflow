import { bootstrapApplication } from '@angular/platform-browser';
import { RouteReuseStrategy, provideRouter, withPreloading, PreloadAllModules } from '@angular/router';
import { provideHttpClient, withInterceptors } from '@angular/common/http';
import { IonicRouteStrategy, provideIonicAngular } from '@ionic/angular/standalone';
import { addIcons } from 'ionicons';
import {
  layers, addCircle, search, hammerOutline,
  logOutOutline, trashOutline, createOutline,
  cubeOutline, folderOpenOutline, addOutline,
  construct, cameraOutline, locationOutline,
  chevronBack, arrowBack, chevronBackOutline,
} from 'ionicons/icons';

import { AppComponent } from './app/app.component';
import { appRoutes } from './app/app.routes';
import { authInterceptor } from './app/interceptors/auth.interceptor';

addIcons({
  layers, 'add-circle': addCircle, search, 'hammer-outline': hammerOutline,
  'log-out-outline': logOutOutline, 'trash-outline': trashOutline,
  'create-outline': createOutline, 'cube-outline': cubeOutline,
  'folder-open-outline': folderOpenOutline, 'add-outline': addOutline,
  construct, 'camera-outline': cameraOutline, 'location-outline': locationOutline,
  'chevron-back': chevronBack, 'arrow-back': arrowBack,
  'chevron-back-outline': chevronBackOutline,
});

bootstrapApplication(AppComponent, {
  providers: [
    { provide: RouteReuseStrategy, useClass: IonicRouteStrategy },
    provideIonicAngular(),
    provideRouter(appRoutes, withPreloading(PreloadAllModules)),
    provideHttpClient(withInterceptors([authInterceptor])),
  ],
}).catch(err => console.error(err));
