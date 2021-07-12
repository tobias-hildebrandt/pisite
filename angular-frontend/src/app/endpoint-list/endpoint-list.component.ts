import { Component, OnInit } from '@angular/core';
import { Endpoint } from '../models';
import { ENDPOINTS } from '../data';

@Component({
  selector: 'app-endpoint-list',
  templateUrl: './endpoint-list.component.html',
  styleUrls: ['./endpoint-list.component.css']
})
export class EndpointListComponent implements OnInit {

  endpoints: Endpoint[] = ENDPOINTS;
  
  constructor() { }

  ngOnInit(): void {
  }

  updateEndpoints() {
    //TODO: update all endpoint components
  }

}
