import { ComponentFixture, TestBed } from '@angular/core/testing';

import { ExecutionsComponent } from './executions.component';

describe('ExecutionsComponent', () => {
  let component: ExecutionsComponent;
  let fixture: ComponentFixture<ExecutionsComponent>;

  beforeEach(async () => {
    await TestBed.configureTestingModule({
      imports: [ExecutionsComponent]
    })
    .compileComponents();

    fixture = TestBed.createComponent(ExecutionsComponent);
    component = fixture.componentInstance;
    fixture.detectChanges();
  });

  it('should create', () => {
    expect(component).toBeTruthy();
  });
});
