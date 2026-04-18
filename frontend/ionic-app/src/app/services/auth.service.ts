import { Injectable } from '@angular/core';
import { HttpClient } from '@angular/common/http';
import { Router } from '@angular/router';
import { tap } from 'rxjs/operators';
import { environment } from '../../environments/environment';

export interface AuthUser {
  id: string;
  username: string;
  email: string;
}

const TOKEN_KEY = 'scrap_token';
const USER_KEY  = 'scrap_user';

@Injectable({ providedIn: 'root' })
export class AuthService {
  private base = environment.apiUrl;

  constructor(private http: HttpClient, private router: Router) {}

  get token(): string | null {
    return localStorage.getItem(TOKEN_KEY);
  }

  get currentUser(): AuthUser | null {
    const raw = localStorage.getItem(USER_KEY);
    return raw ? JSON.parse(raw) : null;
  }

  get isLoggedIn(): boolean {
    return !!this.token;
  }

  register(username: string, email: string, password: string) {
    return this.http.post<{ access_token: string; user: AuthUser }>(
      `${this.base}/api/auth/register`, { username, email, password }
    ).pipe(tap(res => this.store(res)));
  }

  login(email: string, password: string) {
    return this.http.post<{ access_token: string; user: AuthUser }>(
      `${this.base}/api/auth/login`, { email, password }
    ).pipe(tap(res => this.store(res)));
  }

  logout() {
    localStorage.removeItem(TOKEN_KEY);
    localStorage.removeItem(USER_KEY);
    this.router.navigate(['/landing'], { replaceUrl: true });
  }

  private store(res: { access_token: string; user: AuthUser }) {
    localStorage.setItem(TOKEN_KEY, res.access_token);
    localStorage.setItem(USER_KEY, JSON.stringify(res.user));
  }
}
