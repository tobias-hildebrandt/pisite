import { ComponentFixture, TestBed } from '@angular/core/testing';

import { ShowTestComponent } from './show-test.component';

describe('ShowTestComponent', () => {
  let component: ShowTestComponent;
  let fixture: ComponentFixture<ShowTestComponent>;

  beforeEach(async () => {
    await TestBed.configureTestingModule({
      declarations: [ ShowTestComponent ]
    })
    .compileComponents();
  });

  beforeEach(() => {
    fixture = TestBed.createComponent(ShowTestComponent);
    component = fixture.componentInstance;
    fixture.detectChanges();
  });

  it('should create', () => {
    expect(component).toBeTruthy();
  });
});
