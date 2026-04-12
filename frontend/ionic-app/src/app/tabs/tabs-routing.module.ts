import { NgModule } from '@angular/core';
import { RouterModule, Routes } from '@angular/router';
import { TabsPage } from './tabs.page';

const routes: Routes = [
  {
    path: 'tabs',
    component: TabsPage,
    children: [
      {
        path: 'inventory',
        loadChildren: () => import('../inventory/inventory.module').then(m => m.InventoryPageModule)
      },
      {
        path: 'inventory/:id',
        loadChildren: () => import('../item-detail/item-detail.module').then(m => m.ItemDetailPageModule)
      },
      {
        path: 'add',
        loadChildren: () => import('../add/add.module').then(m => m.AddPageModule)
      },
      {
        path: 'search',
        loadChildren: () => import('../search/search.module').then(m => m.SearchPageModule)
      },
      {
        path: '',
        redirectTo: '/tabs/inventory',
        pathMatch: 'full'
      }
    ]
  },
  {
    path: '',
    redirectTo: '/tabs/inventory',
    pathMatch: 'full'
  }
];

@NgModule({
  imports: [RouterModule.forChild(routes)],
})
export class TabsPageRoutingModule {}
