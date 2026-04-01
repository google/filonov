import { Component, inject } from '@angular/core';
import { FormsModule } from '@angular/forms';
import { MediaTaggingService } from './../../services/media-tagging.service';

@Component({
  selector: 'app-tagging',
  imports: [FormsModule],
  templateUrl: './tagging.component.html',
  styleUrl: './tagging.component.css',
})
export class TaggingComponent {
  private taggingService = inject(MediaTaggingService);
  taggers: string[] = ['gemini', 'gcloud'];
  tagger: string = 'gemini';
  mediaTypes: string[] = [
    'image',
    'video',
    'youtube_video',
    'webpage',
    'youtube_thumbnail',
    'text',
  ];
  mediaType: string = 'youtube_video';
  mediaPaths: string = '';

  tag() {
    const mediaPathsSplitted = this.mediaPaths.split(/[\r\n]+/);
    this.taggingService
      .tagMedia(this.tagger, this.mediaType.toUpperCase(), mediaPathsSplitted)
      .subscribe((response) => console.log(response));

    console.log(this.tagger, this.mediaType, mediaPathsSplitted);
  }
}
