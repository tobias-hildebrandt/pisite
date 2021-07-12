import { NgModule } from '@angular/core';
import { BrowserModule } from '@angular/platform-browser';

import { AppRoutingModule } from './app-routing.module';
import { AppComponent } from './app.component';

import { HttpClientModule } from '@angular/common/http';

import { ShowTestComponent } from './show-test/show-test.component';
import { EndpointComponent } from './endpoint/endpoint.component';
import { EndpointListComponent } from './endpoint-list/endpoint-list.component';

@NgModule({
  declarations: [
    AppComponent,
    ShowTestComponent,
    EndpointComponent,
    EndpointListComponent,
  ],
  imports: [
    BrowserModule,
    AppRoutingModule,
    HttpClientModule
  ],
  providers: [],
  bootstrap: [AppComponent]
})
export class AppModule { }
