import { ComponentFixture, TestBed } from '@angular/core/testing';
import { ServiceWorkerModule } from '@angular/service-worker';
import { IonicModule } from '@ionic/angular';
import { IonicStorageModule, Storage } from '@ionic/storage-angular';
import { HistoryPage } from './history.page';

describe('HistoryPage', () => {
  let component: HistoryPage;
  let fixture: ComponentFixture<HistoryPage>;

  beforeEach(async () => {
    await TestBed.configureTestingModule({
      declarations: [HistoryPage],
      imports: [
        IonicModule.forRoot(),
        IonicStorageModule.forRoot(),
        ServiceWorkerModule.register('', { enabled: false }),
      ],
    }).compileComponents();

    const storage = TestBed.inject(Storage);
    await storage.create();

    fixture = TestBed.createComponent(HistoryPage);
    component = fixture.componentInstance;
    fixture.detectChanges();
  });

  it('should create', () => {
    expect(component).toBeTruthy();
  });
});
