// import { Button } from "@/components/ui/button"
// import {
//   Dialog,
//   DialogClose,
//   DialogContent,
//   DialogDescription,
//   DialogFooter,
//   DialogHeader,
//   DialogTitle,
//   DialogTrigger,
// } from "@/components/ui/dialog"

// const DialogButton = ({children}: {children: React.ReactNode}) => {
//   return (
//     <Dialog>
//       <form>
//         <DialogTrigger asChild>
//           {children}
//         </DialogTrigger>
//         <DialogContent className="sm:max-w-[425px]">
//           <DialogHeader>
//             <DialogTitle>Edit profile</DialogTitle>
//             <DialogDescription>
//               Make changes to your profile here. Click save when you&apos;re
//               done.
//             </DialogDescription>
//           </DialogHeader>
          
//           <DialogFooter>
//             <DialogClose asChild>
//               <Button variant="outline">Cancel</Button>
//             </DialogClose>
//             <Button type="submit">Save changes</Button>
//           </DialogFooter>
//         </DialogContent>
//       </form>
//     </Dialog>
//   )
// }

// export default DialogButton

import { Button } from '@/components/ui/button';
import {
  Dialog,
  DialogClose,
  DialogContent,
  DialogDescription,
  DialogFooter,
  DialogHeader,
  DialogTitle,
  DialogTrigger,
} from '@/components/ui/dialog';

interface DialogButtonProps {
  children: React.ReactNode;         // Trigger button
  content: React.ReactNode;          // DialogContent body
  title?: string;
  description?: string;
}

const DialogButton = ({
  children,
  content,
  title = 'Dialog Title',
  description = '',
}: DialogButtonProps) => {
  return (
    <Dialog>
      <DialogTrigger asChild>{children}</DialogTrigger>

      <DialogContent className="sm:max-w-[534px] max-h-[609px] flex flex-col gap-4">
        <DialogHeader className="shrink-0 text-left">
          <DialogTitle>{title}</DialogTitle>
          {description && (
            <DialogDescription>{description}</DialogDescription>
          )}
        </DialogHeader>
        <div className="flex-1 overflow-y-auto min-h-0">
            {content}
        </div>
      </DialogContent>
    </Dialog>
  );
};

export default DialogButton;
