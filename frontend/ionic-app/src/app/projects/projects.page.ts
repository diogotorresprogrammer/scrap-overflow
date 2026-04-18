import { Component } from '@angular/core';
import { DatePipe } from '@angular/common';
import { Router } from '@angular/router';
import {
  IonHeader, IonToolbar, IonTitle, IonButtons, IonButton, IonIcon,
  IonContent, IonSpinner, IonList, IonItemSliding, IonItem, IonLabel,
  IonBadge, IonItemOptions, IonItemOption,
  AlertController, ToastController,
} from '@ionic/angular/standalone';
import { ProjectsService, Project } from '../services/projects.service';

@Component({
  selector: 'app-projects',
  templateUrl: 'projects.page.html',
  styleUrls: ['projects.page.scss'],
  standalone: true,
  imports: [
    DatePipe,
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
      header: 'New project',
      inputs: [
        { name: 'name', placeholder: 'Project name', attributes: { required: true } },
        { name: 'description', placeholder: 'Description (optional)' },
      ],
      buttons: [
        { text: 'Cancel', role: 'cancel' },
        {
          text: 'Create',
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
      header: 'Delete project?',
      message: `"${p.name}" will be permanently removed.`,
      buttons: [
        { text: 'Cancel', role: 'cancel' },
        {
          text: 'Delete', role: 'destructive',
          handler: () => {
            this.svc.deleteProject(p.id!).subscribe({
              next: async () => {
                this.projects = this.projects.filter(x => x.id !== p.id);
                const t = await this.toastCtrl.create({ message: 'Project deleted.', duration: 1500 });
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
