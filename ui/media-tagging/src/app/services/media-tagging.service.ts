import { Injectable, inject } from '@angular/core';
import { HttpClient } from '@angular/common/http';

@Injectable({
  providedIn: 'root'
})
export class MediaTaggingService {
  private httpClient = inject(HttpClient);

  getVersion() {
    return this.httpClient.get<string>('api/version');
  }

  tagMedia(taggerType: string, mediaType: string, mediaPaths: string[]) {
    return this.httpClient.post(
      '/api/tag',
      {
        'tagger_type': taggerType,
        'media_type': mediaType,
        'media_paths': mediaPaths,
      }
    );
  }

  describeMedia(taggerType: string, mediaType: string, mediaPaths: string[]) {
    return this.httpClient.post(
      'describe',
      {
        'tagger_type': taggerType,
        'media_type': mediaType,
        'media_paths': mediaPaths,
      }
    );
  }
}
