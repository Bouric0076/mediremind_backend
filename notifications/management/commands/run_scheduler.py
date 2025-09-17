from django.core.management.base import BaseCommand, CommandError
from django.conf import settings
import logging
import signal
import sys
import time
from notifications.scheduler import start_scheduler, stop_scheduler, get_scheduler_status
from notifications.queue_manager import start_queue_manager, stop_queue_manager, get_queue_health
from notifications.background_tasks import start_background_tasks, stop_background_tasks, get_background_task_status

logger = logging.getLogger(__name__)

class Command(BaseCommand):
    help = 'Run the notification scheduler and queue management system'
    
    def add_arguments(self, parser):
        parser.add_argument(
            '--daemon',
            action='store_true',
            help='Run as daemon process',
        )
        parser.add_argument(
            '--status',
            action='store_true',
            help='Show status of running services',
        )
        parser.add_argument(
            '--stop',
            action='store_true',
            help='Stop running services',
        )
        parser.add_argument(
            '--restart',
            action='store_true',
            help='Restart all services',
        )
        parser.add_argument(
            '--service',
            choices=['scheduler', 'queue', 'background', 'all'],
            default='all',
            help='Specify which service to manage',
        )
        parser.add_argument(
            '--log-level',
            choices=['DEBUG', 'INFO', 'WARNING', 'ERROR'],
            default='INFO',
            help='Set logging level',
        )
    
    def handle(self, *args, **options):
        # Set up logging
        logging.basicConfig(
            level=getattr(logging, options['log_level']),
            format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
        )
        
        service = options['service']
        
        if options['status']:
            self.show_status(service)
            return
            
        if options['stop']:
            self.stop_services(service)
            return
            
        if options['restart']:
            self.stop_services(service)
            time.sleep(2)
            self.start_services(service)
            return
        
        # Default: start services
        self.start_services(service)
        
        if options['daemon']:
            self.run_daemon()
        else:
            self.run_interactive()
    
    def start_services(self, service):
        """Start specified services"""
        try:
            if service in ['scheduler', 'all']:
                self.stdout.write('Starting notification scheduler...')
                start_scheduler()
                self.stdout.write(self.style.SUCCESS('✓ Scheduler started'))
            
            if service in ['queue', 'all']:
                self.stdout.write('Starting queue manager...')
                start_queue_manager()
                self.stdout.write(self.style.SUCCESS('✓ Queue manager started'))
            
            if service in ['background', 'all']:
                self.stdout.write('Starting background tasks...')
                start_background_tasks()
                self.stdout.write(self.style.SUCCESS('✓ Background tasks started'))
                
        except Exception as e:
            raise CommandError(f'Failed to start services: {str(e)}')
    
    def stop_services(self, service):
        """Stop specified services"""
        try:
            if service in ['background', 'all']:
                self.stdout.write('Stopping background tasks...')
                stop_background_tasks()
                self.stdout.write(self.style.SUCCESS('✓ Background tasks stopped'))
            
            if service in ['queue', 'all']:
                self.stdout.write('Stopping queue manager...')
                stop_queue_manager()
                self.stdout.write(self.style.SUCCESS('✓ Queue manager stopped'))
            
            if service in ['scheduler', 'all']:
                self.stdout.write('Stopping notification scheduler...')
                stop_scheduler()
                self.stdout.write(self.style.SUCCESS('✓ Scheduler stopped'))
                
        except Exception as e:
            self.stdout.write(self.style.ERROR(f'Error stopping services: {str(e)}'))
    
    def show_status(self, service):
        """Show status of specified services"""
        self.stdout.write(self.style.HTTP_INFO('=== Notification System Status ===\n'))
        
        if service in ['scheduler', 'all']:
            try:
                status = get_scheduler_status()
                self.stdout.write(self.style.HTTP_INFO('📅 Scheduler Status:'))
                self.stdout.write(f"  Running: {self.format_bool(status['is_running'])}")
                self.stdout.write(f"  Queue Size: {status['queue_size']}")
                self.stdout.write(f"  Processing: {status['processing_size']}")
                self.stdout.write(f"  Active Tasks: {status['active_tasks']}")
                self.stdout.write(f"  Total Processed: {status['stats']['total_processed']}")
                self.stdout.write(f"  Successful: {status['stats']['successful']}")
                self.stdout.write(f"  Failed: {status['stats']['failed']}")
                self.stdout.write('')
            except Exception as e:
                self.stdout.write(self.style.ERROR(f"  Error getting scheduler status: {str(e)}\n"))
        
        if service in ['queue', 'all']:
            try:
                health = get_queue_health()
                self.stdout.write(self.style.HTTP_INFO('🔄 Queue Manager Status:'))
                self.stdout.write(f"  Health Score: {health['health_score']:.1f}%")
                self.stdout.write(f"  Status: {health['status'].upper()}")
                self.stdout.write(f"  Active Queues: {health['active_queues']}/{health['total_queues']}")
                self.stdout.write(f"  Total Processed: {health['total_messages_processed']}")
                self.stdout.write(f"  Pending Messages: {health['total_messages_pending']}")
                self.stdout.write(f"  Avg Processing Time: {health['average_processing_time']:.2f}s")
                self.stdout.write('')
            except Exception as e:
                self.stdout.write(self.style.ERROR(f"  Error getting queue status: {str(e)}\n"))
        
        if service in ['background', 'all']:
            try:
                bg_status = get_background_task_status()
                self.stdout.write(self.style.HTTP_INFO('⚙️  Background Tasks Status:'))
                self.stdout.write(f"  Running: {self.format_bool(bg_status['is_running'])}")
                self.stdout.write(f"  Active Tasks: {bg_status['active_tasks']}")
                self.stdout.write('')
                
                for task_id, task_info in bg_status['tasks'].items():
                    status_icon = "✅" if task_info['enabled'] and not task_info['is_running'] else "🔄" if task_info['is_running'] else "❌"
                    self.stdout.write(f"  {status_icon} {task_info['name']}")
                    self.stdout.write(f"    Enabled: {self.format_bool(task_info['enabled'])}")
                    self.stdout.write(f"    Running: {self.format_bool(task_info['is_running'])}")
                    if task_info['last_run']:
                        self.stdout.write(f"    Last Run: {task_info['last_run']}")
                    if task_info['next_run']:
                        self.stdout.write(f"    Next Run: {task_info['next_run']}")
                    self.stdout.write(f"    Errors: {task_info['error_count']}/{task_info['max_errors']}")
                    self.stdout.write('')
                    
            except Exception as e:
                self.stdout.write(self.style.ERROR(f"  Error getting background task status: {str(e)}\n"))
    
    def format_bool(self, value):
        """Format boolean values with colors"""
        if value:
            return self.style.SUCCESS('Yes')
        else:
            return self.style.ERROR('No')
    
    def run_daemon(self):
        """Run as daemon process"""
        self.stdout.write(self.style.SUCCESS('🚀 Notification system running in daemon mode'))
        self.stdout.write('Press Ctrl+C to stop gracefully')
        
        # Set up signal handlers for graceful shutdown
        def signal_handler(signum, frame):
            self.stdout.write('\n📴 Received shutdown signal, stopping services...')
            self.stop_services('all')
            self.stdout.write(self.style.SUCCESS('✅ All services stopped gracefully'))
            sys.exit(0)
        
        signal.signal(signal.SIGINT, signal_handler)
        signal.signal(signal.SIGTERM, signal_handler)
        
        try:
            # Keep the process alive
            while True:
                time.sleep(60)
                # Optionally log periodic status
                logger.info('Notification system running...')
        except KeyboardInterrupt:
            self.stdout.write('\n📴 Stopping services...')
            self.stop_services('all')
            self.stdout.write(self.style.SUCCESS('✅ All services stopped'))
    
    def run_interactive(self):
        """Run in interactive mode"""
        self.stdout.write(self.style.SUCCESS('🚀 Notification system started'))
        self.stdout.write('\nAvailable commands:')
        self.stdout.write('  status - Show system status')
        self.stdout.write('  restart - Restart all services')
        self.stdout.write('  stop - Stop all services')
        self.stdout.write('  quit - Exit')
        self.stdout.write('\nPress Ctrl+C to stop gracefully\n')
        
        try:
            while True:
                try:
                    command = input('scheduler> ').strip().lower()
                    
                    if command == 'status':
                        self.show_status('all')
                    elif command == 'restart':
                        self.stop_services('all')
                        time.sleep(2)
                        self.start_services('all')
                        self.stdout.write(self.style.SUCCESS('✅ Services restarted'))
                    elif command == 'stop':
                        self.stop_services('all')
                        self.stdout.write(self.style.SUCCESS('✅ Services stopped'))
                    elif command in ['quit', 'exit', 'q']:
                        break
                    elif command == 'help':
                        self.stdout.write('Available commands: status, restart, stop, quit')
                    elif command:
                        self.stdout.write(self.style.ERROR(f'Unknown command: {command}'))
                        
                except EOFError:
                    break
                except Exception as e:
                    self.stdout.write(self.style.ERROR(f'Error: {str(e)}'))
                    
        except KeyboardInterrupt:
            pass
        finally:
            self.stdout.write('\n📴 Stopping services...')
            self.stop_services('all')
            self.stdout.write(self.style.SUCCESS('✅ Goodbye!'))