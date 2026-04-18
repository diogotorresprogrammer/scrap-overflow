import { Component, OnInit } from '@angular/core';
import { DatePipe } from '@angular/common';
import { FormsModule } from '@angular/forms';
import { ActivatedRoute } from '@angular/router';
import {
  IonHeader, IonToolbar, IonButtons, IonBackButton, IonTitle, IonButton,
  IonIcon, IonSpinner, IonContent, IonList, IonItem, IonLabel,
  IonInput, IonTextarea, IonSelect, IonSelectOption, IonBadge, IonNote,
  AlertController, NavController, ToastController,
} from '@ionic/angular/standalone';
import { ProjectsService, Project, ProjectStatus } from '../services/projects.service';

@Component({
  selector: 'app-project-detail',
  templateUrl: 'project-detail.page.html',
  styleUrls: ['project-detail.page.scss'],
  standalone: true,
  imports: [
    FormsModule, DatePipe,
    IonHeader, IonToolbar, IonButtons, IonBackButton, IonTitle, IonButton,
    IonIcon, IonSpinner, IonContent, IonList, IonItem, IonLabel,
    IonInput, IonTextarea, IonSelect, IonSelectOption, IonBadge, IonNote,
  ],
})
export class ProjectDetailPage implements OnInit {
  project: Project | null = null;
  draft: Partial<Project> = {};
  loading = true;
  saving = false;
  editing = false;

  readonly statuses: { value: ProjectStatus; label: string }[] = [
    { value: 'planning',    label: 'Planning' },
    { value: 'in_progress', label: 'In progress' },
    { value: 'completed',   label: 'Completed' },
    { value: 'cancelled',   label: 'Cancelled' },
  ];

  constructor(
    private route: ActivatedRoute,
    private svc: ProjectsService,
    private nav: NavController,
    private alertCtrl: AlertController,
    private toastCtrl: ToastController,
  ) {}

  ngOnInit() {
    const id = this.route.snapshot.paramMap.get('id')!;
    this.svc.getProject(id).subscribe({
      next: (p) => { this.project = p; this.loading = false; },
      error: () => { this.loading = false; },
    });
  }

  startEdit() {
    this.draft = { ...this.project };
    this.editing = true;
  }

  cancelEdit() {
    this.editing = false;
    this.draft = {};
  }

  save() {
    this.saving = true;
    this.svc.updateProject(this.project!.id!, this.draft).subscribe({
      next: async (updated) => {
        this.project = updated;
        this.editing = false;
        this.saving = false;
        const t = await this.toastCtrl.create({ message: 'Saved.', duration: 1500 });
        await t.present();
      },
      error: () => { this.saving = false; },
    });
  }

  async confirmDelete() {
    const alert = await this.alertCtrl.create({
      header: 'Delete project?',
      message: `"${this.project!.name}" will be permanently removed.`,
      buttons: [
        { text: 'Cancel', role: 'cancel' },
        { text: 'Delete', role: 'destructive', handler: () => this.delete() },
      ],
    });
    await alert.present();
  }

  private delete() {
    this.svc.deleteProject(this.project!.id!).subscribe({
      next: () => this.nav.navigateBack('/tabs/projects'),
    });
  }

  statusColor(status: string | undefined): string {
    const map: Record<string, string> = {
      planning: 'medium', in_progress: 'primary', completed: 'success', cancelled: 'danger',
    };
    return map[status ?? ''] ?? 'medium';
  }
}
