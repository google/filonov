import { ComponentFixture, TestBed } from '@angular/core/testing';

import { TaggingComponent } from './tagging.component';

describe('TaggingComponent', () => {
  let component: TaggingComponent;
  let fixture: ComponentFixture<TaggingComponent>;

  beforeEach(async () => {
    await TestBed.configureTestingModule({
      imports: [TaggingComponent]
    })
    .compileComponents();

    fixture = TestBed.createComponent(TaggingComponent);
    component = fixture.componentInstance;
    fixture.detectChanges();
  });

  it('should create', () => {
    expect(component).toBeTruthy();
  });
});
