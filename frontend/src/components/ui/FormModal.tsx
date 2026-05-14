import Modal from "./modal";
import { Button } from "./button";

type FormModalProps = {
  isOpen: boolean;
  onClose: () => void;
  onSubmit: () => void | Promise<void>
  title: string;
  type: "add" | "edit";
  children: React.ReactNode;
  isLoading?: boolean;
  submitLabel?: string;
};

export const FormModal = ({ isOpen, onClose, onSubmit, title, type, children, isLoading, submitLabel }: FormModalProps) => {
  const actionLabel = submitLabel ?? (type === "add" ? "Add Transaction" : "Save Changes");
  return (
    <Modal
      isOpen={isOpen}
      onClose={onClose}
      title={title}
      variant={type === "add" ? "success" : "default"}
      size="sm"
      footer={
        <div className="flex justify-end gap-3">
          <Button variant="secondary" onClick={onClose} disabled={isLoading}>
            Cancel
          </Button>
          <Button 
            variant={type === "add" ? "success" : "primary"} 
            onClick={onSubmit}
            disabled={isLoading}
          >
            {actionLabel}
          </Button>
        </div>
      }
    >
      {children}
    </Modal>
  );
};
