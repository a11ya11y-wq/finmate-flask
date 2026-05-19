import Modal from "./modal";
import { Button } from "./button"; 

type ConfirmDeleteModalProps = {
  isOpen: boolean;
  onClose: () => void;
  onConfirm: () => void;
  title?: string;
  description?: string;
  isLoading?: boolean;
};

export const ConfirmDeleteModal = ({ 
  isOpen, 
  onClose, 
  onConfirm, 
  title = "Delete Transaction",
  description = "Are you sure you want to delete this item? This action cannot be undone.",
  isLoading 
}: ConfirmDeleteModalProps) => {
  return (
    <Modal
      isOpen={isOpen}
      onClose={onClose}
      title={title}
      variant="danger"
      size="sm"
      footer={
        <div className="flex justify-end gap-3">
          <Button variant="secondary" onClick={onClose} disabled={isLoading}>
            Cancel
          </Button>
          <Button 
            className="bg-rose-500 hover:bg-rose-600 text-white" 
            onClick={onConfirm}
            disabled={isLoading}
          >
            {isLoading ? "Deleting..." : "Delete"}
          </Button>
        </div>
      }
    >
      <div className="flex flex-col gap-4">
        <p className="text-slate-200">{description}</p>
        <div className="flex items-start gap-3 rounded-xl border border-rose-500/20 bg-rose-500/10 p-4 text-sm text-rose-400">
          <i className="bi bi-exclamation-triangle-fill mt-0.5" />
          <p>This action will permanently remove the data from your history.</p>
        </div>
      </div>
    </Modal>
  );
};
