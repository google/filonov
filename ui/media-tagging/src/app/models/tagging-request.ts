export interface MediaTaggingRequest {
  taggerType: string;
  mediaType: string;
  mediaPaths: string[];
  deduplicate: boolean;
}
