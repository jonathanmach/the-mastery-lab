import { Injectable } from '@nestjs/common';

export interface User {
  id: number;
  name: string;
}

const userList = [
  { id: 1, name: 'John Doe' },
  { id: 2, name: 'Jane Doe' },
];

@Injectable()
export class AppService {
  getHello(): string {
    return 'Hello World!';
  }

  getUsers(): User[] {
    return userList;
  }
}
