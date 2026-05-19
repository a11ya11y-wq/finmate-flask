

export interface RegisterRequest {
    username: string; // min=4 max=32
    password: string; // min=6 max=32
    confirmPassword: string; // =password
    email: string; // valid email format
}

export interface RegisterField {
    name: 'username' | 'email' | 'password' | 'confirmPassword';
}