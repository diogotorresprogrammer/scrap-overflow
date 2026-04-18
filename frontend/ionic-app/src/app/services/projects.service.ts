import { Injectable } from '@angular/core';
import { HttpClient } from '@angular/common/http';
import { Observable } from 'rxjs';
import { environment } from '../../environments/environment';

export type ProjectStatus = 'planning' | 'in_progress' | 'completed' | 'cancelled';

export interface Project {
  id?: string;
  name: string;
  description?: string;
  status?: ProjectStatus;
  created_at?: string;
  completed_at?: string | null;
}

@Injectable({ providedIn: 'root' })
export class ProjectsService {
  private base = `${environment.apiUrl}/api/projects`;

  constructor(private http: HttpClient) {}

  getProjects(): Observable<Project[]> {
    return this.http.get<Project[]>(this.base);
  }

  createProject(p: Partial<Project>): Observable<Project> {
    return this.http.post<Project>(this.base, p);
  }

  getProject(id: string): Observable<Project> {
    return this.http.get<Project>(`${this.base}/${id}`);
  }

  updateProject(id: string, changes: Partial<Project>): Observable<Project> {
    return this.http.patch<Project>(`${this.base}/${id}`, changes);
  }

  deleteProject(id: string): Observable<void> {
    return this.http.delete<void>(`${this.base}/${id}`);
  }
}
