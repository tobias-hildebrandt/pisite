import { Component, OnInit } from '@angular/core';
import { Endpoint } from '../models';
import { RequesterService } from '../requester.service';

@Component({
  selector: 'app-show-test',
  templateUrl: './show-test.component.html',
  styleUrls: ['./show-test.component.css']
})
export class ShowTestComponent implements OnInit {

  test: string = "not yet updated";
  

  constructor(private requesterService: RequesterService) { }

  ngOnInit(): void {
  }

  updateTest() {
    this.requesterService.getTest().subscribe((response) => {
      if (response.success) {
        this.test = JSON.stringify(response.data);
      }
    });
  }

}
