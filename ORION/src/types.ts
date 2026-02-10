export interface HistoryItem {
  url: string;
  title: string;
  timestamp: number;
}

export interface BookmarkItem {
  id: string;
  url: string;
  title: string;
  timestamp: number;
}

export interface DownloadItem {
  id: string;
  filename: string;
  totalBytes: number;
  receivedBytes: number;
  state: 'progressing' | 'completed' | 'cancelled' | 'interrupted';
  path?: string;
}

export interface InteractiveElement {
  tag: string;
  text: string;
  selector: string;
  type: 'clickable' | 'input';
}

export interface PageScanResult {
  title: string;
  description: string;
  headings: string[];
  interactive: InteractiveElement[];
}
