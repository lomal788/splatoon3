// 코어 → 화면/소리 쪽 단방향 이벤트. 프레임마다 비우며, 결정 로직은 이벤트에 의존하지 않는다.
// 이벤트 이름은 원본 xlink 키나 의미가 드러나는 이름을 쓰고 DESIGN.md "이벤트" 표에 등록한다.
export interface GameEvent {
  type: string;
  [k: string]: unknown;
}

export class EventQueue {
  list: GameEvent[] = [];
  emit(e: GameEvent): void {
    this.list.push(e);
  }
  clear(): void {
    this.list.length = 0;
  }
}
