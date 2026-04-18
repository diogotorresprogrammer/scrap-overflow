import { Routes } from '@angular/router';
import { authGuard } from './guards/auth.guard';

export const appRoutes: Routes = [
  {
    path: 'landing',
    loadComponent: () => import('./landing/landing.page').then(m => m.LandingPage),
  },
  {
    path: 'tabs',
    loadComponent: () => import('./tabs/tabs.page').then(m => m.TabsPage),
    canActivate: [authGuard],
    children: [
      {
        path: 'inventory',
        loadComponent: () => import('./inventory/inventory.page').then(m => m.InventoryPage),
      },
      {
        path: 'inventory/:id',
        loadComponent: () => import('./item-detail/item-detail.page').then(m => m.ItemDetailPage),
      },
      {
        path: 'add',
        loadComponent: () => import('./add/add.page').then(m => m.AddPage),
      },
      {
        path: 'search',
        loadComponent: () => import('./search/search.page').then(m => m.SearchPage),
      },
      {
        path: 'projects',
        loadComponent: () => import('./projects/projects.page').then(m => m.ProjectsPage),
      },
      {
        path: 'projects/:id',
        loadComponent: () => import('./project-detail/project-detail.page').then(m => m.ProjectDetailPage),
      },
      {
        path: '',
        redirectTo: 'inventory',
        pathMatch: 'full',
      },
    ],
  },
  {
    path: '',
    redirectTo: '/landing',
    pathMatch: 'full',
  },
];
