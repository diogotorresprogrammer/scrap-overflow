import { Injectable } from '@angular/core';
import { BehaviorSubject } from 'rxjs';

const KEY = 'scrap_user_id';

@Injectable({ providedIn: 'root' })
export class UserService {
  private id$ = new BehaviorSubject<string | null>(localStorage.getItem(KEY));

  get userId(): string | null {
    return this.id$.value;
  }

  set(id: string) {
    localStorage.setItem(KEY, id);
    this.id$.next(id);
  }

  clear() {
    localStorage.removeItem(KEY);
    this.id$.next(null);
  }
}
