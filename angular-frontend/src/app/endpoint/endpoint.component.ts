import { Component, Input, OnInit } from '@angular/core';
import { Endpoint, PowerStatus } from '../models';
import { RequesterService } from '../requester.service';

@Component({
  selector: 'app-endpoint',
  templateUrl: './endpoint.component.html',
  styleUrls: ['./endpoint.component.css']
})
export class EndpointComponent implements OnInit {

  @Input() endpoint?: Endpoint;
  status: string = "uninitialized";

  constructor(private requesterService: RequesterService) { }

  ngOnInit(): void {
  }

  updateStatus() {
    if (!this.endpoint) return;

    this.requesterService.getStatus(this.endpoint).subscribe((response) => {
      if (!response.success) {
        this.status = `error: ${response.message}`
      } else {
        this.status = JSON.stringify(response.data);
      }
    });
  }

}
