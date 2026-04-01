import { Component } from '@angular/core';

@Component({
  selector: 'app-executions',
  imports: [],
  templateUrl: './executions.component.html',
  styleUrl: './executions.component.css'
})
export class ExecutionsComponent {

  executions: string[] = ['test', 'test2'];

}
