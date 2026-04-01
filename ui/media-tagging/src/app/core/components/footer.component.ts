import { Component, inject } from '@angular/core';
import { MediaTaggingService } from './../../services/media-tagging.service';

@Component({
  selector: 'app-footer',
  imports: [],
  templateUrl: 'footer.component.html'
})
export class FooterComponent {
  private mediaTaggingService = inject(MediaTaggingService);
  version: string = '';

  ngOnInit() {
    this.mediaTaggingService.getVersion().subscribe((version) => (this.version = version));
  }
}
