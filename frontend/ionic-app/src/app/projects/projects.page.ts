import { Component } from '@angular/core';
import { DatePipe } from '@angular/common';
import { Router } from '@angular/router';
import {
  IonHeader, IonToolbar, IonTitle, IonButtons, IonButton, IonIcon,
  IonContent, IonSpinner, IonList, IonItemSliding, IonItem, IonLabel,
  IonBadge, IonItemOptions, IonItemOption,
  AlertController, ToastController,
} from '@ionic/angular/standalone';
import { TranslatePipe, TranslateService } from '@ngx-translate/core';
import { ProjectsService, Project } from '../services/projects.service';

@Component({
  selector: 'app-projects',
  templateUrl: 'projects.page.html',
  styleUrls: ['projects.page.scss'],
  standalone: true,
  imports: [
    DatePipe, TranslatePipe,
    IonHeader, IonToolbar, IonTitle, IonButtons, IonButton, IonIcon,
    IonContent, IonSpinner, IonList, IonItemSliding, IonItem, IonLabel,
    IonBadge, IonItemOptions, IonItemOption,
  ],
})
export class ProjectsPage {
  projects: Project[] = [];
  loading = true;

  constructor(
    private svc: ProjectsService,
    private router: Router,
    private alertCtrl: AlertController,
    private toastCtrl: ToastController,
    private translate: TranslateService,
  ) {}

  ionViewWillEnter() { this.load(); }

  load() {
    this.loading = true;
    this.svc.getProjects().subscribe({
      next: (p) => { this.projects = p; this.loading = false; },
      error: () => { this.loading = false; },
    });
  }

  goToDetail(p: Project) {
    this.router.navigate(['/tabs/projects', p.id]);
  }

  async promptCreate() {
    const alert = await this.alertCtrl.create({
      header: this.translate.instant('projects.new-project'),
      inputs: [
        { name: 'name', placeholder: this.translate.instant('projects.project-name-placeholder'), attributes: { required: true } },
        { name: 'description', placeholder: this.translate.instant('projects.description-optional-placeholder') },
      ],
      buttons: [
        { text: this.translate.instant('common.cancel'), role: 'cancel' },
        {
          text: this.translate.instant('common.create'),
          handler: (d) => {
            if (!d.name?.trim()) return false;
            this.svc.createProject({ name: d.name.trim(), description: d.description || undefined }).subscribe({
              next: (p) => {
                this.projects.unshift(p);
                this.router.navigate(['/tabs/projects', p.id]);
              },
            });
            return true;
          },
        },
      ],
    });
    await alert.present();
  }

  async deleteProject(p: Project) {
    const alert = await this.alertCtrl.create({
      header: this.translate.instant('projects.delete-confirm-header'),
      message: this.translate.instant('projects.delete-confirm-message', { name: p.name }),
      buttons: [
        { text: this.translate.instant('common.cancel'), role: 'cancel' },
        {
          text: this.translate.instant('common.delete'), role: 'destructive',
          handler: () => {
            this.svc.deleteProject(p.id!).subscribe({
              next: async () => {
                this.projects = this.projects.filter(x => x.id !== p.id);
                const t = await this.toastCtrl.create({
                  message: this.translate.instant('projects.deleted'),
                  duration: 1500,
                });
                await t.present();
              },
            });
          },
        },
      ],
    });
    await alert.present();
  }

  statusColor(status: string | undefined): string {
    const map: Record<string, string> = {
      planning: 'medium', in_progress: 'primary', completed: 'success', cancelled: 'danger',
    };
    return map[status ?? ''] ?? 'medium';
  }
}
