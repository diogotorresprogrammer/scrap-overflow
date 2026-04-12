import { Injectable } from '@angular/core';
import { HttpClient, HttpParams } from '@angular/common/http';
import { Observable } from 'rxjs';
import { environment } from '../../environments/environment';

export type ItemType = 'item' | 'lumber' | 'metal' | 'furniture' | 'appliance';

export interface ScrapItem {
  id?: string;
  user_id?: string;
  item_type?: ItemType;
  name: string;
  description?: string;
  dimension_raw?: string;
  dimension_parsed?: Record<string, unknown>;
  dimension_unit?: string;
  tags?: string[];
  location_lat?: number;
  location_lng?: number;
  location?: { lat: number; lng: number } | null;
  condition?: string;
  photo_url?: string;
  created_at?: string;
  // allocation
  allocated?: boolean;
  project_id?: string | null;
  allocated_at?: string | null;
  consumed?: boolean;
  consumed_at?: string | null;
  // donation
  is_donation?: boolean;
  donator_id?: string | null;
  donated_at?: string | null;
  // lumber
  species?: string;
  length?: number;
  width?: number;
  thickness?: number;
  grade?: string;
  is_treated?: boolean;
  // metal
  metal_type?: string;
  profile?: string;
  alloy?: string;
  // furniture
  furniture_type?: string;
  material?: string;
  style?: string;
  num_pieces?: number;
  has_hardware?: boolean;
  // appliance
  appliance_type?: string;
  brand?: string;
  model_number?: string;
  working_condition?: string;
  voltage?: number;
  amperage?: number;
}

@Injectable({ providedIn: 'root' })
export class ApiService {
  private base = environment.apiUrl;

  constructor(private http: HttpClient) {}

  getItems(filters?: { type?: string; user_id?: string }): Observable<ScrapItem[]> {
    let params = new HttpParams();
    if (filters?.type) params = params.set('type', filters.type);
    if (filters?.user_id) params = params.set('user_id', filters.user_id);
    return this.http.get<ScrapItem[]>(`${this.base}/api/items`, { params });
  }

  createItem(item: Partial<ScrapItem>): Observable<ScrapItem> {
    return this.http.post<ScrapItem>(`${this.base}/api/items`, item);
  }

  getItem(id: string): Observable<ScrapItem> {
    return this.http.get<ScrapItem>(`${this.base}/api/items/${id}`);
  }

  updateItem(id: string, changes: Partial<ScrapItem>): Observable<ScrapItem> {
    return this.http.patch<ScrapItem>(`${this.base}/api/items/${id}`, changes);
  }

  deleteItem(id: string): Observable<void> {
    return this.http.delete<void>(`${this.base}/api/items/${id}`);
  }
}
