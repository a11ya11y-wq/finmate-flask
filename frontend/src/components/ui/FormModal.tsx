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
};

export const FormModal = ({ isOpen, onClose, onSubmit, title, type, children, isLoading }: FormModalProps) => {
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
            {type === "add" ? "Add Transaction" : "Save Changes"}
          </Button>
        </div>
      }
    >
      {children}
    </Modal>
  );
};
