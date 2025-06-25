import { LucideIcon } from 'lucide-react';
import { Card, CardContent } from '@/components/ui/card';
import { cn } from '@/lib/utils';

interface StatsCardProps {
  icon: LucideIcon;
  value: string;
  label: string;
  color?: 'primary' | 'secondary' | 'success' | 'warning';
}

const colorVariants = {
  primary: 'bg-primary/10 text-primary border-primary/20',
  secondary: 'bg-secondary/10 text-secondary-foreground border-secondary/20',
  success: 'bg-green-50 text-green-700 border-green-200 dark:bg-green-950/30 dark:text-green-400 dark:border-green-800',
  warning: 'bg-amber-50 text-amber-700 border-amber-200 dark:bg-amber-950/30 dark:text-amber-400 dark:border-amber-800',
};

const StatsCard = ({ icon: Icon, value, label, color = 'primary' }: StatsCardProps) => {
  return (
    <Card className={cn('glass-effect hover:shadow-md transition-all duration-200', colorVariants[color])}>
      <CardContent className="p-4 text-center">
        <div className="flex flex-col items-center space-y-2">
          <Icon className="w-5 h-5" />
          <div>
            <div className="text-lg font-bold">{value}</div>
            <div className="text-xs opacity-75">{label}</div>
          </div>
        </div>
      </CardContent>
    </Card>
  );
};

export default StatsCard; 